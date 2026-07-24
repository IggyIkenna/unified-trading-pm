---
doc_type: plan
title: Data-Pipeline Hardening + Self-Monitoring — Shipped History (forked from the hardening/self-monitoring plan)
summary:
  Archive-bound Progress Log history extracted verbatim from data_pipeline_hardening_self_monitoring_2026_06_22.md's
  2026-07-24 line-cap remediation split (2nd pass). Covers the fully-shipped, dated Progress Log narrative from "ALERT
  SPAM REDUCTION" through the "TradFi databento outbound-call hardening" entry (2026-06-22 to 2026-06-24) —
  alert-spam-reduction, self-heal/agent-escalation loop closure, watch-the-watchers SPOF closure, the import-crash
  incident, fleet-wide build-caching rollout, and the tradfi databento hang incident. Every item in this file is already
  checked-off `[x]` or pure narrative — zero open todos. Record-only; not intended for further action.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [data-pipeline, hardening, monitoring, history, plan-split, archive-bound]
related: [/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-24 from data_pipeline_hardening_self_monitoring_2026_06_22.md's Progress Log tail during the
    2nd-pass line-cap trim (parent still over the 2000-line umbrella cap after the first 3-way + 1-issue split).",
  ]
locked_by:
locked_since:
---

> **🟢 2026-07-24 history extraction** — this file holds Progress Log content moved VERBATIM out of
> `data_pipeline_hardening_self_monitoring_2026_06_22.md` (the "ALERT SPAM REDUCTION" section through the final "TradFi
> databento outbound-call hardening" entry) to bring that plan back under its 2000-line umbrella cap. Every line below
> already existed in the parent unchanged — no content was altered, only relocated. All items here are
> shipped/`[x]`/pure narrative; there are no open todos in this file. See the parent plan for current status, the
> failure catalogue, and the still-open items.

# Data-Pipeline Hardening + Self-Monitoring — Shipped History

## Progress Log — ALERT SPAM REDUCTION (verbose→baselined, 2026-06-22/23)

- **Channel triage** (operator showed the live #data-pipeline-alerts): the system WORKS (real findings — a hung
  tradfi-bf-cme VM after ApiKeyReloader, a silent sports VM, defi divergent-empty, schema-not-v9 — all via the real
  router/notifier path; watcher read 39 healthy VMs ALIVE, no false flood). Now reducing spam.
- **Fix 1 — digest 5×→1 union** (e2e@949fdc3): `data_pipeline_daily_digest.py` was emitting `DP_DAILY_DIGEST` per-AG
  (5/day); now ONE union emit `{message:"5 AGs: cefi X% …", per_ag, asset_groups}`. Unit test asserts call_count==1.
  **DEPLOYED + VERIFIED**: e2e-audit image rebuilt (Cloud Build 119abbf1 SUCCESS), 3 audit jobs re-resolved `:latest`,
  digest executed → exit(0), 1m47s.
- **Fix 2 — detail richness** (e2e@949fdc3): every `emit_dp_event` in digest/hygiene/reprobe now carries `asset_group` +
  a one-line `message` (e.g. `DP_NOT_V9` → "cefi: schema_version_not_v9 1/4 rows non-v9"), so alerts render
  distinguishably instead of bare `[DP_NOT_V9] DP_NOT_V9`. (The bare 3×/13× floods were mostly LEGIT-DISTINCT findings —
  3 AGs not-v9, 13 stalled VMs — that only LOOKED like dupes because details weren't rendering.)
- **Fix 3 — deep-links** : SM secret `DEPLOYMENT_UI_BASE_URL=https://deployment-dashboard-cldtjniqvq-an.a.run.app`
  created (alerting config_reloader hot-reloads it) → the VM-logs/Deployment/Data-status deep-link buttons now render
  (were suppressed when base="").

> **Residual forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md`: verify the heartbeat-stall
> watcher emit carries `vm_name`+`asset_group`+`message`.

## Progress Log — SELF-HEAL + AGENT-ESCALATION LOOP CLOSED (code) 2026-06-23

- **Root cause why no agent ever picked up a finding**: `file_escalation_issue` wrote an issue doc with NO `assigned_vm`
  → `PlanRegenLoop` ONLY ingests `issues/*.md` with an explicit `assigned_vm` → the findings alerted but never became
  backlog tasks. FIXED.
- **FIX 1 — DP_VM_STALL self-heal** (deployment-service@1b529e4): new `scripts/recovery/relaunch_stalled_vm.py`
  actuator + registered `DP_VM_STALL→_recover_stalled_vm` in `_DP_RECOVERY_ACTIONS` (≤2 relaunches/(vm-prefix,day) then
  page; idempotent; never fire-and-forget). So a hung VM (the tradfi-bf-cme stall) auto-relaunches instead of falling
  through. (DP_EVENT_LOOP_STARVED stays file_issue — never-emitting = code bug.)
- **FIX 2 — actionable issues** (deployment-service@1b529e4 + e2e@2d262a9): both issue writers now emit frontmatter
  `parent_epic: observability_master` + `assigned_vm: vm-cross-cutting` + a `- [ ] [CODE] P1` todo naming the target
  repo (VM-lifecycle→deployment-service; data-correctness/not-v9/divergence→MTDS) → PlanRegenLoop→backlog→AutoSpawn → a
  worker fixes it.
- **FIX 3 — fast CI-parity auto-spawn** (deployment-service@1b529e4): `route_finding` best-effort
  `repository_dispatch escalate-to-orchestrator(wall_type=data_pipeline_failure)` for CRITICAL/file_issue findings, auth
  via SM `GH_PAT`, soft-gated (never breaks the finding). Same path CI failures use.
- **DEPLOY status (code-complete, deploying)**: e2e half → e2e-audit image rebuilding (Cloud Build ce6a88e4) →
  re-resolve audit jobs. deployment-service FIX1/FIX3 → the MONITORS run on `deployment-api:latest`, so they go live
  when deployment-api's image rebuilds (rides LDR→staging→main promotion; can expedite).
- [x] ✅ [CODE] P2. **launcher-for-vm registry** — deployment-service@3045b7f:
      `deployment_service/data_pipeline_monitors/launcher_registry.py` maps all 189 `VM_PREFIX_TO_BUCKET` prefixes →
      `scripts/vm/launch-*.sh` (118 to a launcher, 71 explicit `None`+reason for fan-out/singleton/non-backfill);
      `resolve_launcher_for_vm(vm)` does longest-prefix match (fail-safe None→file_issue). Wired into both fleet-monitor
      sweeps (see INFRA todo above) → AUTO-RELAUNCH fires vs file_issue. Guard test
      `tests/unit/test_launcher_registry.py` (7 tests): every watchdog prefix has a registry entry + every non-None
      launcher file exists + bidirectional parity + `tradfi-bf-cme-ohlcv-1m-*` resolves non-None. QG green (64s). Repo:
      deployment-service.

## Progress Log — FINISHING THE DEPLOY (self-heal/escalation live) 2026-06-23

- **(A) e2e audits LIVE**: e2e-audit image rebuilt (Cloud Build ce6a88e4 SUCCESS), 3 audit jobs (digest/hygiene/reprobe)
  re-resolved → the e2e findings (DP_NOT_V9 / DP_DIVERGENT_EMPTY / reprobe) now file ACTIONABLE issues
  (assigned_vm:vm-cross-cutting + a `- [ ]` todo → PlanRegenLoop→AutoSpawn→agent), and the digest emits ONE union event.
- **(C) launcher-for-vm registry SHIPPED** deployment-service@3045b7f: `launcher_registry.py` maps all 189
  `VM_PREFIX_TO_BUCKET` prefixes (118→launcher / 71→None+reason), wired into BOTH `exit_code_fleet_monitor.sweep` +
  `heartbeat_stall_watcher.sweep` (was passing None) → a stalled/OOM VM finding now carries `relaunch_launcher` so the
  `relaunch_stalled_vm`/`relaunch_backfill_vm` actuators ACTUALLY relaunch (bounded ≤2/vm-day, idempotent, never
  fire-and-forget). Guard test: every prefix has a registry entry or explicit None.
- **(B) deployment-api image NOT YET LIVE (correction 2026-06-23)** — my manual build was misread (d536c823 was an
  alerting-service build) AND `deployment-api:latest` is gated to the `deployment-api-main-deploy` trigger
  (`_DEPLOY=true`, `_BRANCH=main`) — a build-only submit is a deploy no-op. The monitor re-resolve picked up the SAME
  old digest. FIX1/FIX3+C go live only when deployment-service@3045b7f promotes LDR→staging→main →
  deployment-api-main-deploy auto-builds+deploys → monitors re-resolve. Original:: the VM monitors run on
  `deployment-api:latest` (which bundles deployment-service via a pre-build rsync). Triggered the rebuild (Cloud Build
  d536c823) from the LDR workspace → on SUCCESS the 3 monitor jobs (exit-code/heartbeat/meta) re-resolve to it, making
  FIX1/FIX3 + the launcher registry LIVE on the monitors. (If the manual build fails the rsync prep, the changes ride
  the LDR→staging→main promotion → deployment-api main-deploy → monitors automatically.)
- **End-state when B lands**: detect → (auto_recover: relaunch consolidator/stalled-VM/OOM-VM, key-rotate, backoff) OR
  (file_issue: actionable plan-todo → AutoSpawn agent) OR (page) — the full CI-parity self-heal + agent-escalation loop,
  continuous without us.

## Progress Log — LOOP LIVE (audit half) + VM-monitor half rides promotion (2026-06-23)

- **FULL self-heal + agent-escalation loop is now DEPLOYED + RUNNING** across both runtimes (e2e-audit image for the
  daily audits; deployment-api image for the VM monitors). Continuous without us: detect → auto_recover (relaunch
  consolidator/stalled-VM/OOM-VM via the launcher registry, key-rotate, backoff) OR file_issue (actionable plan-todo →
  PlanRegenLoop → AutoSpawn data_pipeline_failure agent) OR page; CRITICAL also fast-dispatches
  escalate-to-orchestrator. The hung tradfi-bf-cme VM class now auto-relaunches; the defi divergent-empty / not-v9
  findings now reach an agent. **Deploy status (corrected): e2e-audit ce6a88e4 IS deployed (3 audit jobs on the new
  image — the e2e half is LIVE). deployment-api is NOT yet redeployed (gated to main-deploy); the 3 monitor jobs still
  run the prior image until deployment-service@3045b7f reaches main → deployment-api-main-deploy. So the AUDIT-side loop
  is live; the VM-MONITOR-side self-heal/dispatch rides the promotion.**

## Progress Log — LOOP LIVE END-TO-END (VERIFIED, 2026-06-23)

- **(B) deployment-api DEPLOYED + VERIFIED**: `deployment-api-build` trigger on LDR (Cloud Build de72c709) SUCCESS →
  `deployment-api:latest` digest CHANGED `sha256:084b690…`→`sha256:e0f81fac…` (genuinely new image, not the prior no-op
  trap) → 3 monitor jobs (exit-code/heartbeat/meta) re-resolved. FIX1 (self-heal actuators) + FIX3 (fast
  escalate-to-orchestrator dispatch) + the launcher registry are now LIVE on the VM monitors.
- **FULL LOOP LIVE (both halves verified)**: audit half (e2e-audit, digest changed earlier) + VM-monitor half
  (deployment-api, digest changed now). detect → auto_recover (relaunch consolidator/stalled-VM/OOM-VM via the launcher
  registry, key-rotate, backoff) OR file_issue (actionable plan-todo → PlanRegenLoop → AutoSpawn data_pipeline_failure
  agent) OR page; CRITICAL also fast-dispatches escalate-to-orchestrator. Continuous without us.
- **Deploy-honesty note**: the `:latest` digest is the verification of record for "deployed" (a build SUCCESS alone is
  NOT deployed — the earlier d536c823 was an alerting-service build + the deployment-api `:latest` is gated to its build
  trigger, not a raw `gcloud builds submit`). Always re-resolve Cloud Run jobs AFTER confirming the digest changed.

## Watch-the-watchers SPOF — meta-monitoring gap (surfaced 2026-06-23 by operator Q "can the monitoring itself go down?")

**Finding (audit-verified):** the pipeline + zombie-watchdog + catalogue enumerator + consolidator each have a
dead-man's-switch (DP-CATALOG-001 / DP-WATCHER-001 / DP-WATCHER-002), BUT the fleet-monitor crons and the
alerting-service relay have NO external watcher → the monitoring CAN silently go down. The meta-watcher is the top of
the chain and nothing watches it. No `google_monitoring_alert_policy` in terraform; `retry_count=0` on the fleet-monitor
scheduler jobs. Evidence: `meta_watchers.check_cron_fired` only targets the consolidator availability_index;
`data_pipeline_fleet_monitor_scheduler.tf` retry_count=0; no notification_channel resource fleet-wide.

- [x] ✅ [CODE] P0. **Cron-watches-cron (in-band closure).** Each fleet-monitor sweep (`exit-code`/`heartbeat`/`meta`)
      writes `vm-census/<mode>-last-run.json` at end-of-sweep (`_gcs.write_monitor_last_run`); the meta sweep runs
      `meta_watchers.check_monitor_crons_fired` (a `FreshnessTarget` per sentinel via `monitor_cron_targets`, budget =
      2× cadence — 10m for `*/5`, 30m for `*/15`); a stale/absent sentinel fires `DP_CRON_DID_NOT_FIRE` (DP-WATCHER-002,
      CRITICAL/page). The meta sweep can't catch its OWN death this way — Layer-2 owns that. —
      deployment-service@fda68cf | QG green (56s) | tests: test_data_pipeline_deadman.py (Layer-1 roundtrip +
      staleness→DP-WATCHER-002, 5 tests pass).
- [x] ✅ [INFRA] P0. **Out-of-band dead-man's-switch (the top-of-chain watcher).**
      `deployment_service.data_pipeline_monitors.deadman_poster` + `terraform/gcp/monitoring_deadman_scheduler.tf`
      (`uts-prod-monitoring-deadman` Cloud Run job on `deployment-api:latest`, own `*/15` Cloud Scheduler,
      `retry_count=2`). Each tick reads every monitor sentinel freshness + `lifecycle-events-sub`
      `oldest_unacked_message_age` (Cloud Monitoring API, >30m ⇒ subscriber/relay down) and on ANY staleness posts
      DIRECTLY to SM `MONITORING_DEADMAN_SLACK_WEBHOOK` — DELIBERATELY independent of PubSub/alerting/`log_event`/the
      #data-pipeline-alerts webhook (namespace unit test enforces). Terminal bedrock: `google_monitoring_alert_policy`
      on the deadman job's OWN execution-failure → a `google_monitoring_notification_channel` of type **email**
      (`ikenna@odum-research.com` — operator-chosen 2026-06-23; a deliberately DIFFERENT mechanism from Slack = true
      defense-in-depth; `# TODO(operator): optionally swap to native Slack` — needs interactive OAuth). Registry entry
      added (`cloud_run_job_registry.py` guard). — deployment-service@fda68cf (email corrected in follow-up) | QG green
      | `tofu validate` Success | tests: 10 deadman tests pass. **`tofu apply` operator/infra-gated — apply pending.**

## Progress Log — watch-the-watchers SPOF CLOSED in code (2026-06-23)

- **Both layers shipped** to deployment-service@fda68cf (QG exit 0, 15 deadman unit tests pass, `tofu fmt`+`validate`
  clean): Layer-1 cron-watches-cron sentinels + `check_monitor_crons_fired`; Layer-2 independent `monitoring-deadman`
  Cloud Run job + poster (posts to SM `MONITORING_DEADMAN_SLACK_WEBHOOK`, namespace-test-enforced independence from
  PubSub/alerting); bedrock `google_monitoring_alert_policy` → email channel; `retry_count=2` on the 3 fleet-monitor
  schedulers.
- **Email bedrock target = `ikenna@odum-research.com`** (operator 2026-06-23) — corrected from the agent's
  `iggy2london@gmail.com` default. **Mechanism = GCP-native email** (Cloud Monitoring sends it directly), NOT
  Resend/Firebase: the bedrock must survive our entire stack being down, so it cannot route through our code/API-keys
  (Resend is correctly the UI's transactional-email tool, wrong for a monitoring backstop). Defense-in-depth ladder:
  Layer-1→#data-pipeline-alerts (our relay) · Layer-2→#monitoring-deadman (independent webhook) · bedrock→GCP-native
  email (no Slack, no our-code).
- **ONLY operator action remaining**: `tofu apply` the two new resources (`monitoring_deadman_scheduler.tf` + the
  fleet-monitor `retry_count` bump) — deliberately not auto-applied (infra-gated). Optional: one-time OAuth to swap the
  bedrock email channel to native Slack.
- [x] ✅ [INFRA] P1. Set `retry_count=2` on the 3 fleet-monitor scheduler jobs in
      `data_pipeline_fleet_monitor_scheduler.tf` so a transient Cloud Run invocation failure does not silently drop a
      tick. — deployment-service@fda68cf.

## Progress Log — codex drift closed + SPOF captured (2026-06-23)

- **Codex made authoritative** (consistency audit of plans+codex+deployment-observability): added DP-PATH-006
  (`DP_BARE_INSTRUMENT_KEY_UNRESOLVED`) + DP-RATE-003 (`sports_adapter_429`) rows to `data-pipeline-alerts.md` (were
  registry.yaml-only); documented the **Self-heal actuator layer** (`_DP_RECOVERY_ACTIONS` map + 3 relaunch scripts +
  `launcher_registry.py` ~189-prefix resolver); marked the `file_escalation_issue` e2e half **PARTIAL** (code-complete,
  not yet quickmerged); added the **Watching the watchers** section with the honest KNOWN-SPOF + closure plan.
- **Audit verdicts**: plans = CONSISTENT (no unflipped shipped items); deployment-observability = CONSISTENT
  (resolver/registry/endpoints/channel all agree across CLAUDE.md+codex+plan); codex = was DRIFT on the 3 items above,
  now closed.
- **SPOF answer to operator**: monitoring is NOT yet fully self-watching — P0 closure todos filed above
  (cron-watches-cron in-band + GCP-native out-of-band dead-man's-switch).

## Progress Log — watch-the-watchers DMS APPLIED to prod (2026-06-23)

- **`tofu apply` DONE** (operator-authorized 2026-06-23; targeted to MY resources only — full plan showed a foreign
  drift backlog of un-applied changes, NOT swept in): `Apply complete! 6 added, 6 changed, 0 destroyed`. Created in prod
  (`central-element-323112` / `terraform/state/prod`): `uts-prod-monitoring-deadman` Cloud Run job + `*/15` scheduler +
  `monitoring_deadman_down` alert policy + `monitoring_deadman_email` notification channel (→
  ikenna@odum-research.com) + monitoring.viewer & SM-webhook-accessor IAM for `unified-trading-sa`. Changed:
  `retry_count=2` on the 3 fleet-monitor schedulers.
- **TWO completion steps:** (1) **image rebuild IN FLIGHT** — `deployment-api-build` build `cd879efe` rebuilds
  `deployment-api:latest` from LDR (clones deployment-service@LDR fresh → includes deadman_poster + cli.py sentinel
  writes + meta_watchers.check_monitor_crons_fired); on SUCCESS, re-resolve the 6 monitor/audit jobs + the new deadman
  job to the new digest (the running :latest=e0f81fac predates fda68cf). (2) **operator: click the GCP
  email-verification link** sent to ikenna@odum-research.com — the bedrock notification channel won't deliver until
  verified.

> **Excised 2026-07-24** (mis-filed — general prod-infra terraform drift, not a data-pipeline-hardening concern) →
> `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`: reconcile the prod terraform drift backlog (21 add / 18
> change, `terraform/state/prod`).

## INCIDENT 2026-06-23 — monitors crashed at import (caught by EXECUTING, not digest)

Root cause: `escalation.py` imported the Layer-0 actuators at module level via `from scripts.recovery.* import …`, but
`scripts/recovery/` is NOT in the installed `deployment_service` wheel (the deployment-api image installs the package
then drops the source). → `data_pipeline_monitors/__init__.py` crashed at load → EVERY monitor job + the deadman died
(exit 1 ImportError). **This was live since the FIX1 actuator deploy and missed because that "deploy" was verified by
digest-change ONLY, never by executing a job.** Lesson reinforced: deployed≠running — execute the job, read the exit
code.

- [x] ✅ [CODE] P0. **Load-safe + runtime-safe actuator import.** `escalation.py`:
      `_ACTUATORS_AVAILABLE = importlib.util.find_spec(...)` at load + `importlib.import_module(...)` inside each
      dispatch fn (dynamic call, not an `import` stmt → passes no-imports-inside-functions gate AND ruff). Actuators
      absent → `status=UNAVAILABLE` → degrade to `file_issue`, never crash. +regression test
      `test_route_auto_recover_actuators_unavailable_falls_through`. — deployment-service@(quickmerged) | QG exit 0
      (53s) | 17 tests pass.

> **Residual forked 2026-07-24** → `data_pipeline_self_healing_completion_residual_2026_07_24.md`: package the self-heal
> actuators (+ launchers) into the runtime image so `auto_recover` can actually actuate from the Cloud Run monitors.

- [x] ✅ [VERIFY] P0. **Monitors + deadman EXECUTE exit 0 — PROVEN (2026-06-23).** After the probe fix (find_spec
      raise-safe), all 4 jobs (`uts-prod-dp-exit-code-monitor` / `-heartbeat-watcher` / `-meta-watchers` /
      `-monitoring-deadman`) re-resolved to the probe-fixed `deployment-api:latest` and EXECUTED with
      `succeededCount=1 / failedCount=0`. Verified by actually running each job + reading the execution exit code (NOT a
      digest check). The watch-the-watchers DETECTION half (Layer-1 cron-watches-cron + Layer-2 deadman + GCP bedrock
      email→ikenna@odum-research.com, channel VERIFIED) is now LIVE.
  - **Root-cause chain (for the record):** (1) module-level `from scripts.recovery…` crashed every monitor in the
    wheel-only image; (2) the find_spec capability probe I added ALSO crashed — `find_spec` RAISES `ModuleNotFoundError`
    (not returns None) when the parent `scripts.recovery` is absent and a top-level `scripts` exists (the image ships
    deployment-api's own `/app/scripts`); fixed by catching that narrow error in `_probe_actuators_available()`. Both
    were caught only by EXECUTING a job — the lesson: built≠running, read the exit code.
  - **Image-home finding:** the monitors run on the heavy `deployment-api` image (which DROPS `scripts/`), so
    `auto_recover` degrades to escalate there. The lighter `deployment-service` image carries `scripts/recovery` +
    `scripts/vm` + gcloud (would close the actuator gap in-image) but is currently stale/incompatible. Since the
    relaunch goes via escalate-to-orchestrator (operator decision), in-image `scripts/` is not required.
- [x] ✅ [INFRA] P1. **Build caching for deployment-api SHIPPED (operator ask 2026-06-23 — "don't we cache?").** Added
      `DOCKER_BUILDKIT=1` + `--build-arg BUILDKIT_INLINE_CACHE=1` + `--cache-from …:latest` (pulled in pull-base-image
      step) to the `docker build` step — deployment-api@753340c. First build seeds the inline cache; subsequent small
      deployment-service code changes reuse the UI-dist + deps layers (~10min → ~2-3min). Shipped via the
      pipeline-config carve-out (isolated to cloudbuild.yaml; quickmerge was blocked only by FOREIGN dirty deps).
      ORIGINAL: The `deployment-api/cloudbuild.yaml` `docker build` step has NO `--cache-from` and no buildkit/kaniko
      cache → every build redoes the deployment-ui SPA build + vendor-dep clones + `uv pip install` from scratch (~10
      min for a 1-line change). Add `docker pull …/deployment-api:latest || true` then
      `--cache-from …/deployment-api:latest` to the build step (Dockerfile already orders deps-before-source) → a
      deployment-service code change drops to ~2-3 min. Repo: deployment-api.
- [x] ✅ [CODE] P1. **Registry-driven relaunch via escalate-to-orchestrator (operator decision 2026-06-23) — SHIPPED
      deployment-service@3a7d86c (QG exit 0, 19 tests pass; landed on LDR after the foreign UAC peer cleared).** DONE in
      deployment-service (QG exit 0 / 19 tests pass; quickmerge BLOCKED only by FOREIGN dirty deps — peer editing
      UAC+strategy-service — ships the moment they clear): (a) `route_finding` now dispatches escalate-to-orchestrator
      when a WIRED auto_recover actuator could not actuate (UNAVAILABLE in the monitor image / FAILED / budget) — fires
      EVEN with no PM clone on disk (the Cloud Run case), so the relaunch is never stranded; (b)
      `_dispatch_to_orchestrator` client_payload now carries the STRUCTURED relaunch binding (`action=relaunch_vm` +
      `vm_name` + `relaunch_launcher` + `deployment_id` + `asset_group`) so the worker relaunches from the registries
      deterministically; (c) worker runbook `/codex/15-runbooks/incidents/rb_infra_relaunch.md` (read
      DeploymentsRegistry row + launcher_registry → re-run launcher → verify STARTED@60s/PROGRESS@10min →
      ≤2/(prefix,day) bound). Registries used: `deployments_registry.DeploymentsRegistry` +
      `launcher_registry.resolve_launcher_for_vm` + `cloud_run_job_registry.CLOUD_RUN_JOBS`. Stretch (deferred sub-todo
      below): persist the FULL launch CLI args into `DeploymentRegistryEntry` for an exact replay. ORIGINAL: Close the
      actuator-actuation gap NOT by packaging scripts into the monitor image, but by routing the `auto_recover`
      UNAVAILABLE path → the EXISTING `escalate-to-orchestrator` repository_dispatch (`wall_type=data_pipeline_failure`)
      onto a **planning-VM slot** (reuses the working Claude Code auth/bootstrap; migrate to a dedicated VM later). The
      worker has `scripts/vm/launch-*.sh` + `launcher_registry` (vm→launcher) + the `DeploymentsRegistry` row
      (asset_group/task/mode/dates) to relaunch deterministically. Build: (a) the UNAVAILABLE auto_recover result
      escalates-to-orchestrator (not just file_issue) carrying `vm_name` + `relaunch_launcher` + registry
      `deployment_id`; (b) a crisp worker relaunch runbook; (c) optionally persist the full launch spec (CLI args) into
      `DeploymentRegistryEntry` so the relaunch is exact. Repo: deployment-service + a runbook in PM. SSOT registries:
      `cloud_run_job_registry.CLOUD_RUN_JOBS` + `deployments_registry.DeploymentsRegistry` + `launcher_registry`.

> **Residual forked 2026-07-24** → `data_pipeline_self_healing_completion_residual_2026_07_24.md`: stretch — persist the
> full launch spec (CLI args) into `DeploymentRegistryEntry`.

## Fleet-wide build caching (operator ask 2026-06-23 — "apply the speedup to all services")

- [x] ✅ [INFRA] P1. **Build caching rolled out to all 12 standard-shape service repos + service-template (operator ask
      2026-06-23).** New idempotent `scripts/propagation/add-cloudbuild-cache.py` injects `DOCKER_BUILDKIT=1` +
      `--build-arg BUILDKIT_INLINE_CACHE=1` + `--cache-from …:latest` (+ a `:latest` seed-pull in pull-base-image).
      PROVEN on ml-service (build 435094d9 GREEN with caching) BEFORE the fleet sweep; then pushed to
      alerting/batch-live-reconciliation/execution/features/fund-administration/greeks/instruments/market-data-processing/market-tick-data/ml/strategy/trading-agent
      (each `cache-from` verified on origin/LDR). cloudbuild-service-template.yaml patched so new service repos inherit
      it. deployment-api+deployment-service already cached. **Follow-up P2 below** for the 8 different-shape repos.
      ORIGINAL: (today only `deployment-api` + `deployment-service` cache). Pattern = BuildKit inline cache:
      `docker pull …:latest || true` (seed) in pull-base-image + `DOCKER_BUILDKIT=1` env +
      `--build-arg BUILDKIT_INLINE_CACHE=1` + `--cache-from …:latest` on the build step. Mirror `deployment-service`'s
      proven multi-`--target` cache where a Dockerfile is multi-stage. Cloudbuilds are BESPOKE-per-repo ("DO NOT
      auto-generate" header) → apply via a NEW `unified-trading-pm/scripts/propagation/add-cloudbuild-cache.py` (mirror
      `add-cloudbuild-prechecks.py`) + add caching to the 6 `configs/cloudbuild-*-template.yaml` for new repos. **Verify
      on 2-3 heavy-build repos first** (unified-trading-system-ui SPA / ml-service / market-tick-data-service) — confirm
      a build is GREEN + faster — BEFORE the full 22-repo sweep (a bad patch = 22 red CIs).
      Rollout-not-done-until-committed-fleet-wide (per the workflow-template rollout rule). Repos: all + PM templates.
      Provenance: deployment-api caching 2026-06-23.

- [x] ✅ [INFRA] P2. **Build caching DONE for the 8 NON-standard-shape repos (operator ask 2026-06-23) — ALL
      image-building repos now cache.** Breakdown: (a) **3 build NO docker image → caching N/A** (unified-api-contracts
      / e2e-testing / system-integration-tests — 0 `docker build` steps); (b) **args-list shape**
      (unified-trading-system-ui / deployment-ui / client-reporting-api) → `env: [DOCKER_BUILDKIT=1]` +
      `--build-arg BUILDKIT_INLINE_CACHE=1` + `--cache-from …:latest` args — PROVEN GREEN on client-reporting-api build
      3af46a83 (no pull-base needed; BuildKit auto-pulls --cache-from from the registry); (c) **bash-heredoc with
      repo-specific refs** (unified-trading-library: hardcoded UTL image + `EXTRA_PYTHON_INDEX_URL`; ibkr-gateway-infra:
      `Dockerfile.terraform` + `${_TERRAFORM_IMAGE_NAME}`) — same proven pattern as the 12 service repos; (d)
      **templates** `cloudbuild-ui-template.yaml` + `cloudbuild-api-template.yaml` patched so new UI/api repos inherit
      it (service-template already done). Net: every repo that builds a Docker image (22 of 24) now caches; the 3
      image-less repos are correctly N/A. ORIGINAL: (the patcher correctly SKIPs these — different build steps):
      unified-trading-system-ui + deployment-ui (SPA/nginx builds), unified-api-contracts + unified-trading-library +
      ibkr-gateway-infra (library builds), e2e-testing + system-integration-tests (test harnesses),
      client-reporting-api. Each needs a per-shape cache patch (extend `add-cloudbuild-cache.py` with the UI/library/api
      build-step shapes) — the UI SPA build is the BIGGEST single win. Prove-per-shape before pushing. Provenance: fleet
      caching rollout 2026-06-23.

## INCIDENT 2026-06-23 — tradfi-bf VMs CAPTURE then HANG mid-backfill (databento chunk-decode had no per-chunk timeout)

Root cause: tradfi-bf backfill VMs captured real OHLCV fine (e.g. `nyse-2024 date=2024-06-24, 300891 records`) then
FROZE mid-backfill — run.log frozen, heartbeat stale (123m–1395m observed). The databento path-streaming fetch wrapped
only the `get_range()` HTTP call in `asyncio.wait_for` (3600s), but the SYNCHRONOUS chunk-decode loop
`for raw_chunk in dbn_store.to_df(count=N)` (`_iterate_dbn_chunks`) ran on the event loop with NO timeout — a stalled
databento stream mid-`to_df` decode hung the whole VM forever (the unbounded-fetch hang class CLAUDE.md warns about).
Compounding: hung VMs stayed RUNNING → clogged the wave-launcher cap-20 slots → throughput collapsed. Diagnosed + fixed
2026-06-23 (slot·human-planning). SSOT for the 3-part fix: this section +
`/codex/02-data/tradfi-databento-sourcing-ssot.md` § "Operational gotchas".

- [x] ✅ [CODE] P1 (ROOT). **Bound the databento DBN chunk-decode with a per-chunk asyncio timeout.**
      `market-tick-data-service` — `_iterate_dbn_chunks` is now async: each chunk's blocking `next()` on the
      `to_df(count=N)` generator runs in the default executor wrapped in
      `asyncio.wait_for(..., timeout=databento_chunk_timeout_s)` (default 300s, env `MTDS_DATABENTO_CHUNK_TIMEOUT_S`). A
      stalled chunk → `TimeoutError` → shard recorded `attempted_failed` (`DATABENTO_TIMEOUT` classification) → the
      per-date/instrument loop CONTINUES (shard isolation), never a VM-wide hang. Covers the equity (DBEQ) + futures
      (GLBX) + CFE paths (shared loop). +regression test `test_stalled_chunk_decode_times_out_and_loop_continues` (a
      chunk iterator that blocks forever → the call returns with a recorded failure, doesn't hang). —
      market-tick-data-service@7298eb7 | QG exit 0 | 6 streaming tests pass (incl. new stall test). Files:
      `databento_fetch.py` + `databento_adapter.py` (`_get_databento_chunk_timeout_s` + `DATABENTO_TIMEOUT` classify) +
      `config/service_config.py` (`databento_chunk_timeout_s`).
- [x] ✅ [CODE] P2 (DEFENSE). **Auto-kill heartbeat-stalled backfill VMs so hung ones don't clog wave-launcher slots
      (DP-VM-005).** `deployment-service` — `heartbeat_stall_watcher.sweep` now takes an injectable `vm_killer`; a STALL
      that passes the pure guard `should_auto_kill` (backfill-only, NOT live/LONG_LIVED_LIVE, heartbeat/frozen-run.log
      age past `DEFAULT_KILL_MINUTES=45`, env `MTDS_DP_VM_KILL_MINUTES`) is DELETED (reusing the zombie-watchdog
      `_kill_vm` forensics-archiving delete) so the wave-launcher reclaims its cap-20 slot; per-sweep cap (default 5)
      prevents a runaway reaping the fleet; emits `DP_VM_STALL` w/ `recovery_action=auto_kill_stalled_vm`. CLI defaults
      auto-kill ON for `--mode heartbeat` (`--no-auto-kill` to disable). **Dry-run on the LIVE fleet (2026-06-23): 59
      running / 5 stalled → exactly 1 WOULD be killed** (`instr-backfill-sports-xg-…` heartbeat 164m stale ≥45m); the
      other 4 (`tradfi-bf-cme-*` stalled 11–16m) correctly within the alert/relaunch window, NOT reaped; zero
      `mtds-live-*` touched. +6 tests (guard, kill, live-exempt, cap). — deployment-service@710824e | QG exit 0.
- [x] ✅ [CODE] P3. **Fix the DP_CRON_DID_NOT_FIRE FALSE POSITIVE for dp-exit-code-monitor (KEY #4).**
      `deployment-service` — `meta_watchers.check_cron_fired` now cross-checks a stale monitor SENTINEL against the REAL
      Cloud Run **Job** execution history: when a `FreshnessTarget` names a `cloud_run_job` AND the injected
      `execution_history_reader` reports the job's last SUCCEEDED execution within budget, the stale-sentinel alert is
      SUPPRESSED (the cron IS firing — the run.log sentinel write is a lagging/secondary signal). `monitor_cron_targets`
      maps `exit-code/heartbeat/meta` → `dp-exit-code-monitor`/`dp-heartbeat-watcher`/`dp-meta-watchers` stems; cli
      wires `_make_execution_history_reader` (Run v2 `ExecutionsClient.list_executions`, deferred-imported, fail-safe-on
      when unavailable). +4 tests (suppress-when-recent / alert-when-execution-also-stale / alert-on-unknown / stems). —
      deployment-service@710824e | QG exit 0.
- [x] ✅ [INFRA] P1. **MTDS tarball rebuilt from clean LDR so new/relaunched VMs get the P1 timeout fix.** The deployed
      MTDS tarball was at the pre-fix sha `bc31da6`; `refresh_code_tarballs.sh` (clones FRESH from
      origin/live-defi-rollout, clean-by-construction — immune to local foreign WIP) detected MTDS CHANGED →
      `bc31da6→7298eb7` and rebuilt+uploaded the tarball. New tradfi-bf VMs the wave-launcher spins up (and any
      relaunch) now bake the per-chunk timeout. Provenance: tradfi databento backfill-hang remediation 2026-06-23.

## Progress Log — DP_VM_GONE_NO_CAPTURE false-positive fixed: idempotent-preflight benign-skip (2026-06-24)

- [x] ✅ [MONITOR] P1. **`DP_VM_GONE_NO_CAPTURE` false-positive suppressed for idempotent-preflight skip VMs.** Root
      cause: a backfill VM (cefi-bybit-2021 on the 171-VM campaign) found its target shards already fully captured,
      logged `venue=BYBIT date=2021-12-31 — all requested data_types fully covered (atoms ⊆ captured), skipping`, then
      exited with captured 0→0. The classifier treated it as a silent zero and fired `DP_VM_GONE_NO_CAPTURE` (CRITICAL
      noise). VERIFIED: the BYBIT 2021-12-31 manifest = 23 captured + 37 empty_confirmed (60 cells, all resolved, zero
      attempted_failed/expected_unattempted) — skip is CORRECT; alert is pure noise. **Fix (already in-tree, now with
      proof tests):** `_HONEST_ABSENCE_RE` in `deployment_service/data_pipeline_monitors/_gcs.py` extended with
      `r"|all requested data_types fully covered|fully covered \(atoms|atoms ⊆ captured"` so
      `classify_no_capture_reason(log)` returns `NoCaptureReason.HONEST_ABSENCE` → verdict `EXPECTED_NO_CAPTURE` (no
      alert) for these benign idempotent-skip exits. Over-suppression is NOT introduced: a VM with captured=0, no "fully
      covered" marker, and unresolved shards still routes to `NoCaptureReason.SILENT` → `GONE_NO_CAPTURE` (alert fires,
      incident caught). Two proof tests added: (1) `test_no_capture_reason_mtds_idempotent_preflight_skip` →
      `HONEST_ABSENCE` (benign, no alert); (2) `test_no_capture_reason_silent_when_no_signal_or_empty` +
      `test_classify_flat_silent_still_gone_no_capture` → `SILENT` → `GONE_NO_CAPTURE` (alert still fires). All 2523
      unit tests pass. — deployment-service@da4247332db | QG unit-pass (version-alignment drift pre-existing, not
      blocking).

## Progress Log — TradFi databento outbound-call hardening DONE (item 112 defence-in-depth, 2026-06-24, slot·human-planning, Opus 4.8, /autonomous)

- [x] ✅ [MONITOR] P2 (DEFENSE). **Every OTHER outbound Databento SDK call is now bounded so no call can hang a backfill
      VM (item 112 — `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md`).** The LIVE hang site (the DBN
      chunk-decode loop) was already fixed `@afd5296` (`MTDS_DATABENTO_CHUNK_TIMEOUT_S`); this closes the remaining
      defence-in-depth. Audited all 12 databento files; the `databento.Historical(key, gateway)` SDK 0.73 constructor
      accepts **NO timeout kwarg** (hardcodes a 100 s per-read socket timeout, untunable), so each blocking call is
      wrapped in executor + `asyncio.wait_for` (async) / `ThreadPoolExecutor.result(timeout=)` (sync, with
      **`shutdown(wait=False)` on timeout** — a `with`-block exit calls `shutdown(wait=True)` which would itself BLOCK
      on the hung worker, re-introducing the hang). **New env knob `MTDS_DATABENTO_REQUEST_TIMEOUT_S` (default 180 s,
      `service_config.databento_request_timeout_s`)** for short calls. **Call sites bounded:** (1) symbology/DEFINITION
      `timeseries.get_range`+`to_df` (`databento_symbology._fetch_definition_df_for_stype`) → stall emits
      ADAPTER_FETCH_FAILED + returns empty df → per-stype loop continues (shard isolation); (2) `metadata.get_cost`
      (`databento_fetch._emit_payg_spend`) → records `cost_lookup_error=TimeoutError`, never blocks; (3)+(4)
      `batch.list_jobs` ×2 (`databento_batch_jobs._query_key_for_matching_job` + `_lookup_job_in_list`) → key skipped /
      retry; (5) `batch.download` (`_execute_batch_download`, bounded by `timeout_minutes`≥600s floor) → raises
      TimeoutError to the async-executor caller; (6) live WS connect/subscribe **handshake** (`_open_subscriptions` +
      `_start_streaming`) → bounded; the steady-state `stream()` consume loop intentionally LEFT unbounded (runs
      forever). Already-bounded (no change): streaming `get_range` (`_fetch_timeseries_range`,
      `_FETCH_TIMEOUT_S=3600`) + `metadata.list_datasets` warmup (`ThreadPoolExecutor.result`). +6 mocked-SDK unit tests
      (`tests/unit/test_databento_outbound_timeouts.py`, no live creds; each `threading.Event`-blocks a stall + asserts
      RETURN/raise within a generous outer `wait_for`). **PRE-EXISTING (not mine, not fixed — out of scope):** 3 stale
      tests in `tests/market_interface/unit/test_databento_adapter_logic.py`
      (`test_submit_batch_job_dict_response`/`_obj_response`/`test_download_batch_invalid_data_type_raises`) fail on
      baseline HEAD because `batch.submit_job` is now `DatabentoBatchApiBannedError` (subscription lockdown) — they
      predate this change; they sit under `market_interface/**` (excluded from QG basedpyright/ruff) and the QG
      `--no-fix` is green. — market-tick-data-service@2410e712 | QG exit 0.

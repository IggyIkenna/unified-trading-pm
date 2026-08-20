---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE burst (10 LONG_LIVED_LIVE producers, 2026-08-10T00:09-00:10Z) — 1 confirmed detector
  false-positive (fixed), 1 likely stale-registry entry (flagged), 8 producers confirmed genuinely absent (real finding,
  not a detector bug)
summary: >-
  A burst of 10 `DP_CRON_DID_NOT_FIRE` CRITICAL pages fired in `#data-pipeline-alerts` within ~90 seconds
  (2026-08-10T00:09-00:10Z), each claiming a different registered `LONG_LIVED_LIVE` producer prefix has zero running
  instances (DP-LIVE-003, `missing_live_producer_watcher.py`). Root cause of the BURST TIMING is now-explained and
  benign: DP-LIVE-003 is a BRAND-NEW check (added same-day, commit `9c7a8ace`, 2026-08-09T17:49:50Z) gated behind the
  standard `MissTracker` `min_consecutive=2` grace window on the meta sweep's 15-minute cadence — its first two
  qualifying sweeps after deploy (`uts-prod-dp-meta-watchers` executions ending ~23:53Z and ~00:09Z) registered a miss
  for every prefix that was ALREADY absent at deploy time, and on the second sweep every one of them crossed the 2-miss
  threshold simultaneously and paged sequentially (~90s to post 10 Slack messages) — not 10 independent simultaneous
  outages and not a shared crash/timeout bug re-firing. A CONTRIBUTING factor: the same Cloud Run Job
  (`uts-prod-dp-meta-watchers`) had been silently hitting its 300s task timeout on EVERY execution since at least
  2026-08-07T22:50Z (fixed same-day, commit `9bc734fe`, live `gcloud run jobs update --task-timeout=900` + terraform
  backport) — while that regression was live, ANY check running late in the sweep sequence (this one included) would
  never have completed even its first sweep, so DP-LIVE-003's true "first ever completed run" only happened after both
  fixes landed 2026-08-09 evening, explaining why the burst landed as a clean two-sweep pair rather than something
  messier.

  Per-prefix ground truth (GCP `gcloud compute instances list` — 50 instances, ALL RUNNING, zero stopped/terminated; AWS
  `aws ec2 describe-instances` — 2 instances, `agent-orchestrator-vm-1` + `ci-escalation-runner-vm-1`, both running;
  `deployments/active/*.json` registry — 47 entries, none matching any of the 10 prefixes below):

  1. **`agent-orch-planning-vm-` — CONFIRMED FALSE POSITIVE (detector bug, FIXED).** The registered prefix names the
     GCE-based `launch-planning-vm.sh` launcher's output (`agent-orch-planning-vm-{YYYYMMDD}`), but
     `launcher_registry.py`'s own comment marks this "Agent-orchestrator VMs (planning; per-epic REMOVED
     2026-07-24)" and the entry `None` — "operator-owned lifecycle, never auto-relaunch". The real orchestrator is
     now the single static, manually-provisioned AWS EC2 instance `agent-orchestrator-vm-1`
     (`i-0c9b283b31d6b5ca7`, EIP 13.113.200.22, launched 2026-08-09T08:31:10Z, confirmed `running`) — it lives on
     AWS (DP-LIVE-003's census, `cli.py::_list_running_vms`, calls `get_compute_engine_client(provider="gcp", ...)`
     only — structurally GCP-only) AND is not even named `agent-orch-planning-vm-{YYYYMMDD}` any more, so even a
     cross-cloud census would still miss it on name alone. Two independent reasons the registered prefix can never
     be satisfied — not a transient absence.

  2. **`mtds-live-prediction-` — LIKELY a SECOND stale-registry entry (same bug class, weaker evidence — FLAGGED,
     not fixed).** No running/deployed instance matches `mtds-live-prediction-*` anywhere. But
     `scripts/vm/launch-mtds-live-prediction-consolidated.sh` (`VM_PREFIX="mtds-live-prediction-consolidated"`,
     motivated 2026-06-28 as a cost optimization consolidating 4 per-shard VMs into 1) shows a burst of
     `instances.insert`/`instances.delete` cycles 2026-06-27..2026-06-29 and NOTHING since — i.e. the consolidated
     migration was tried for ~2 days and then abandoned. Production prediction live-capture has instead run
     continuously via the OLDER, SEPARATE per-shard launcher (`launch-prediction-live.sh`, prefix `prediction-live-`
     — 3 VMs confirmed `RUNNING` right now: `prediction-live-kalshi-trades-20260803-181821`,
     `prediction-live-polymarket-book-snapshot-5-20260803-182839`, `prediction-live-polymarket-trades-20260803-182520`,
     all launched 2026-08-03, none matching the `mtds-live-prediction-` prefix). Both prefixes are independently
     registered `LONG_LIVED_LIVE` for what functionally looks like the same producer via two alternate deployment
     strategies. Unlike finding 1 there is no explicit "REMOVED"/retirement comment for the consolidated path, so
     this is NOT silently "fixed" the same way — it needs an operator call on whether the consolidated-prediction
     migration was deliberately abandoned (in which case the `mtds-live-prediction-` registry entry should be
     dropped, mirroring finding 1) or should be revived (in which case this is instead evidence of the SAME
     genuine-gap class as findings 3-9 below — worth noting also that `launch-prediction-live.sh`'s 3 running VMs
     cover only 3 of its 4 documented shards; `prediction-live-kalshi-book-snapshot-5-*` is not running either, a
     separate smaller gap outside this doc's 10-prefix scope).

  3. **`mdps-features-live-tradfi-` — GENUINELY ABSENT.** Sibling AGs `mdps-features-live-cefi-` and
     `mdps-features-live-defi-` ARE running right now (`...-cefi-20260807-031648`, `...-defi-20260807-032721`).
     TradFi's own history shows short-lived launch/delete cycles on 2026-08-04 (launched 19:22:48Z, deleted
     19:30:24Z; separately launched 05:42:35Z, deleted 05:51:20Z same day) and NOTHING since — no relaunch in the ~6
     days between then and this finding.

  4. **`mdps-features-live-sports-`, 5. `mdps-features-live-prediction-`, 6. `defi-recursive-`, 8.
  `greeks-compute-live-`,
     9. `strategy-live-` — GENUINELY ABSENT, and more strikingly: ZERO `instances.insert` or `instances.delete`
  audit-log
     events for any of these 5 prefixes in the last 90 days** (query verified working — it correctly surfaced events
     for findings 2/3/7 with the identical filter shape). Not "went down recently" — no evidence any of these 5 have
     ever been operated in this GCP project within the audit-log retention window queried.

  7. **`prediction-arb-detector-` — GENUINELY ABSENT, longer-gone than the check's own motivating example.** Last
     `instances.delete` 2026-06-29T06:19:05Z (~6 weeks before this finding) — longer than the 5-week gap on
     `mtds-live-tradfi-cme-trades-` that motivated building DP-LIVE-003 in the first place
     (`tradfi_live_cme_capture_stopped_2026_08_09.md`, itself relaunched 2026-08-09 and now correctly showing
     `RUNNING` — that prefix is NOT among the 10 alerted here, confirming DP-LIVE-003 is not just uniformly
     false-firing).
status: open
archive_exempt: true
nature: issue
asset_group: [cross-cutting, tradfi, sports, prediction, defi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-monitors,
    dp-live-003,
    dp-cron-did-not-fire,
    false-positive,
    missing-live-producer,
    cross-cloud,
    vm-prefix-registry,
  ]
related:
  [
    /plans/archive/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md,
    /plans/active/issues/dp_live_003_agent_orch_aws_credentials_gap_2026_08_10.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-08-10
author: sub-agent (Claude Code session, dispatched to root-cause + fix the DP_CRON_DID_NOT_FIRE burst)
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-20
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_live_003_agent_orch_aws_credentials_gap_2026_08_10.md,
    deployment-service/deployment_service/data_pipeline_monitors/missing_live_producer_watcher.py,
    deployment-service/deployment_service/data_pipeline_monitors/producer_lifecycle.py,
  ]
source: >-
  Operator-reported: 10 DP_CRON_DID_NOT_FIRE alerts fired within ~90 seconds of each other at 2026-08-10T00:09-00:10Z,
  one already confirmed false-positive (agent-orch-planning-vm-, the real AWS orchestrator VM verified running
  directly). Dispatched to find the detector, verify every prefix's ground truth cross-cloud, root-cause the burst
  timing, and fix what's a genuine detector bug vs. flag what's a genuine live-producer gap.
---

# DP_CRON_DID_NOT_FIRE burst — DP-LIVE-003 (missing_live_producer_watcher)

## The detector

`deployment_service/data_pipeline_monitors/missing_live_producer_watcher.py` (DP-LIVE-003). For every registry prefix
tagged `LifecycleClass.LONG_LIVED_LIVE` (excluding `DeploymentUmbrella.PAPER`), it pages `DP_CRON_DID_NOT_FIRE` when
ZERO currently-running VM names start with that prefix, for `min_consecutive=2` consecutive ~15-minute meta-sweeps (a
short relaunch window never false-pages). The running-VM census (`cli.py::_list_running_vms`) is **GCP-Compute-only** by
construction (`get_compute_engine_client(provider="gcp", project_id=project_id)`) — it structurally cannot see AWS
resources. This is shared with the heartbeat/exit-code/reaper sweeps and was NOT changed (too broad a blast radius for
this fix — see Fixed below).

Added same-day as this incident: commit `9c7a8ace` (2026-08-09T17:49:50Z), motivated by
`tradfi_live_cme_capture_stopped_2026_08_09.md` (`mtds-live-tradfi-cme-trades-` sat deleted 5+ weeks with no page — now
relaunched and correctly excluded from this burst, confirming the check does discriminate real presence).

## Root cause of the burst (timing, not content)

1. `uts-prod-dp-meta-watchers` had been silently hitting its Cloud Run Job **300s task timeout on every execution since
   at least 2026-08-07T22:50Z** (terraform comment, commit `9bc734fe`) — `MissTracker`/`RenagTracker` only `.persist()`
   at the END of a full sweep, so a sweep killed mid-way never advances ANY check running late in the sequence. Fixed
   same-day: live `gcloud run jobs update --task-timeout=900` + terraform backport
   (`data_pipeline_fleet_monitor_scheduler.tf`). Live-verified: `gcloud run jobs describe uts-prod-dp-meta-watchers`
   shows `taskTimeoutSeconds: 900`; recent executions complete in ~8-9 minutes, comfortably under budget.
2. DP-LIVE-003 (`9c7a8ace`) deployed the SAME evening, after the timeout fix. Its very first two fully-completed sweeps
   (`uts-prod-dp-meta-watchers-dmvkj` 23:45:05→23:53:30Z, `uts-prod-dp-meta-watchers-h6jbg` 00:00:07→00:09:13Z) are
   exactly the standard `min_consecutive=2` grace window — first sweep registers miss #1 for every already-absent prefix
   (no page), second sweep registers miss #2 for every STILL-absent prefix → all 10 page together, sequentially, within
   that ~9-minute execution (Slack posting spread ≈ the reported ~90s window).
3. This is the deterministic, EXPECTED behavior of any brand-new absence-detector's cold start, not a shared crash or
   re-fire bug across 10 independent conditions — but it does NOT mean the 10 underlying conditions are all false; each
   needed independent ground-truth verification (below).

## Per-prefix ground truth

See summary frontmatter for the full evidence per prefix. Table form:

| #   | Prefix                           | Verdict                                                                    | Evidence                                                                                                                                                     |
| --- | -------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `agent-orch-planning-vm-`        | **FALSE POSITIVE — FIXED**                                                 | Stale GCP-VM registry entry for a per-epic architecture removed 2026-07-24; real orchestrator is a static AWS EC2 instance, wrong cloud AND wrong name       |
| 2   | `mtds-live-prediction-`          | **LIKELY stale registry (2nd instance of bug class) — FLAGGED, not fixed** | Consolidated-migration launch/delete burst 2026-06-27..29 then abandoned; prod runs the separate `prediction-live-` prefix instead (3 VMs currently running) |
| 3   | `mdps-features-live-tradfi-`     | **Genuinely absent**                                                       | Deleted 2026-08-04, never relaunched (~6 days at time of finding)                                                                                            |
| 4   | `mdps-features-live-sports-`     | **Genuinely absent**                                                       | 0 insert/delete events in 90d                                                                                                                                |
| 5   | `mdps-features-live-prediction-` | **Genuinely absent**                                                       | 0 insert/delete events in 90d                                                                                                                                |
| 6   | `defi-recursive-`                | **Genuinely absent**                                                       | 0 insert/delete events in 90d                                                                                                                                |
| 7   | `prediction-arb-detector-`       | **Genuinely absent**                                                       | Deleted 2026-06-29, never relaunched (~6 weeks at time of finding)                                                                                           |
| 8   | `greeks-compute-live-`           | **Genuinely absent**                                                       | 0 insert/delete events in 90d                                                                                                                                |
| 9   | `strategy-live-`                 | **Genuinely absent**                                                       | 0 insert/delete events in 90d                                                                                                                                |
| 10  | `mtds-live-defi-`                | **Genuinely absent**                                                       | 0 insert/delete events in 90d                                                                                                                                |

## Fixed

`deployment_service/data_pipeline_monitors/missing_live_producer_watcher.py` +
`tests/unit/test_missing_live_producer_watcher.py` — added `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` (currently just
`agent-orch-planning-vm-`) excluded from `live_producer_prefixes()`, with 2 new regression tests. Scoped narrowly to
DP-LIVE-003 only — did NOT touch the shared `_list_running_vms()` census (used by heartbeat/exit-code/reaper sweeps too;
adding AWS support there is a materially bigger, riskier change than this incident needs) and did NOT touch
`VM_PREFIX_TO_BUCKET`/`LifecycleClass` (UAC-shared, feeds deployment-ui Monitor tabs). Repo: deployment-service.
Evidence: `quality-gates.sh --no-fix` ALL PASSED (287s), sentinel `4f7983fc8a9a75c4e1f1ab6d093661fa67006c15`; shipped
`deployment-service@be725b0277781b4b3f9d7609254ab82ea9ef4467` via quickmerge (landed on `live-defi-rollout`).

## NOT fixed — deliberately flagged, per this task's scope

**8 producers (findings 3-10) are confirmed genuinely absent from both GCP and AWS right now** — this is a real
data/execution-pipeline gap, not a detector bug, and NOT something to silently relaunch without understanding each
producer's current operational intent (per workspace rule: a VM launch is a bigger decision than this task's scope).
Several read as "never operated in the 90-day audit window" rather than "recently died," which may mean these
`LONG_LIVED_LIVE` registrations were made ahead of an actual production rollout (worth checking against pre-live-trading
status — CLAUDE.md references "before live trading starts" as a live, current state) rather than a regression — but that
is exactly the kind of judgment call this doc should surface, not resolve.

## Todos

- [x] ✅ [SCRIPT] P1. **RESOLVED (2026-08-10 follow-up session)** — finding 2 (`mtds-live-prediction-`) is SUPERSEDED,
      not revived: the 2026-06-27..29 consolidated-launcher migration was tried for ~2 days then abandoned (a burst of
      `instances.insert`/`instances.delete` cycles then nothing since); production prediction live-capture has run
      continuously since via the separate, older `prediction-live-` prefix (`launch-prediction-live.sh`, 3 VMs confirmed
      `RUNNING`, launched 2026-08-03), which is already registered as its own `LONG_LIVED_LIVE` prefix in
      `vm_prefix_registry.VM_PREFIX_TO_BUCKET`. Classified `SUPERSEDED` in the new
      `deployment_service.data_pipeline_monitors.producer_lifecycle.SUPERSEDED_PREFIXES` (see Part 2 below) —
      `mtds-live-prediction-` is excluded from DP-LIVE-003's must-be-running evaluation but left unchanged in
      `VM_PREFIX_TO_BUCKET` itself (a comment there now cross-references this doc) so other consumers (deployment-ui
      Monitor tabs, heartbeat/exit-code/zombie-watchdog) are unaffected. Evidence:
      `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d` (quality-gates.sh --no-fix ALL PASSED, 314s;
      `tests/unit/test_missing_live_producer_watcher.py::test_superseded_producer_absent_never_pages`). Repo:
      deployment-service.
- [x] ✅ [SCRIPT] P1. **PARTIALLY RESOLVED (2026-08-10 follow-up session)** — 6 of the 8 confirmed-genuinely-absent
      producers (findings 4/5/6/8/9/10: `mdps-features-live-sports-`, `mdps-features-live-prediction-`,
      `defi-recursive-`, `greeks-compute-live-`, `strategy-live-`, `mtds-live-defi-`) are classified `NOT_YET_ACTIVE` in
      the new `producer_lifecycle.NOT_YET_ACTIVE_PREFIXES` (Part 2 below) — every one has ZERO
      `instances.insert`/`instances.delete` audit-log events in the 90-day retention window (never operated at all, not
      "recently stopped"), matching the operator's confirmation that these are pre-live-trading placeholders ("expensive
      to run live with no real money at stake yet"). DP-LIVE-003 no longer evaluates these as must-be-running; their
      absence will never page. The remaining 2 (findings 3/7: `mdps-features-live-tradfi-`, `prediction-arb-detector-`)
      have CONFIRMED real operational history (a past launch/delete cycle — regression- shaped, not
      rollout-ahead-shaped) and are deliberately left classified `ACTIVE`/alerting per the fail-toward- alerting rule —
      see the NEW narrower operator todo below for just these 2. Evidence:
      `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`. Repo: deployment-service.
- [x] ✅ [OPERATOR] P1. **RESOLVED (2026-08-19, escalation `agt-7f6044`)** — `mdps-features-live-tradfi-` half of this
      todo. DP-LIVE-003 paged again for this prefix (live-verified zero running instances via `gcloud`); escalated the
      still-open decision via `/blocked` (options: A relaunch now vs B mark `not_yet_active`/`superseded`). Operator
      chose **B**: deliberately not relaunching TradFi live features yet. Reclassified
      `mdps-features-live-tradfi-` from ACTIVE to `NOT_YET_ACTIVE` in `producer_lifecycle.NOT_YET_ACTIVE_PREFIXES` —
      DP-LIVE-003 no longer pages on its absence. New regression tests added covering both directions (must NOT page
      when absent; the remaining ambiguous producer below still MUST page). — deployment-service@16b45256
      (`quality-gates.sh --no-fix` ALL PASSED, 3647 tests; shipped via quickmerge, landed on `live-defi-rollout`,
      ancestry-verified against origin).
- [x] ✅ [OPERATOR] P1. **RESOLVED (2026-08-20, escalation `agt-66493f`, `/blocked` `BLK-adfa52fd`)** —
      `prediction-arb-detector-` half of this todo. Operator chose **A**: reclassify `NOT_YET_ACTIVE` in
      `producer_lifecycle.NOT_YET_ACTIVE_PREFIXES` — deliberate pause, not a regression. DP-LIVE-003 no longer pages on
      its absence. Regression test flipped (`test_prediction_arb_detector_reclassified_not_yet_active`,
      `test_prediction_arb_detector_absent_never_pages`) to assert the new NOT_YET_ACTIVE behavior. —
      deployment-service@27e9f53cd4 (`quality-gates.sh --no-fix` ALL PASSED; shipped via quickmerge, landed on
      `live-defi-rollout`, ancestry-verified against origin).
- [x] ✅ [SCRIPT] P1. **RESOLVED (2026-08-10 follow-up session)** — finding 1's `agent-orch-planning-vm-` exclusion was
      a same-day stopgap (blanket `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` exclusion); it now has a REAL, dedicated AWS EC2
      liveness check (`missing_live_producer_watcher._agent_orch_planning_vm_present`, via a new
      `deployment_service.backends.aws_census.describe_ec2_instance_state` seam — deferred boto3, honest degradation) —
      filters by the orchestrator's Elastic IP (`13.113.200.22`, resilient to the instance ever being replaced) with the
      instance id (`i-0c9b283b31d6b5ca7`) as a belt-and-braces cross-check. Live-verified in this session with real AWS
      CLI credentials: `aws ec2 describe-instances --region ap-northeast-1 --instance-ids i-0c9b283b31d6b5ca7` correctly
      reports `State.Name=running`, `PublicIpAddress=13.113.200.22` — the check's logic is genuinely correct. **BUT a
      real, confirmed blocker remains for PRODUCTION activation**: see the new issue doc
      `dp_live_003_agent_orch_aws_credentials_gap_2026_08_10.md` — the `uts-prod-dp-meta-watchers` Cloud Run Job that
      runs this detector has ZERO AWS credentials wired in (confirmed via
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `environment_variables` block — GCP-only — and the SAME
      documented gap already called out in `cost_snapshot_scheduler.tf`'s AWS cost-slice comment). In production today
      this check will call `aws_census.describe_ec2_instance_state`, get a `NoCredentialsError`, and honestly degrade to
      `None` — DP-LIVE-003 SKIPS the prefix every sweep (never pages, never falsely reports present) — functionally
      identical to the prior blanket-exclusion state for now, but the code path is real, tested, and will self- activate
      the moment credentials are provisioned (no further code change needed). `agent-orch-planning-vm-` was also REMOVED
      from `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` (now empty) since it has its own dedicated resolver. Evidence:
      `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`. Repo: deployment-service.
- [x] ✅ [SCRIPT] P2. **CONFIRMED (ag-closeout-audit cross-cutting 2026-08-10, iterative-drain round)** — live
      `gcloud compute instances list --filter="name~'prediction-live-kalshi-book-snapshot-5'"` returns zero instances,
      GCP project `central-element-323112`: `prediction-live-kalshi-book-snapshot-5-*` (the 4th documented
      `launch-prediction-live.sh` shard) is confirmed not running, matching finding 2's evidence. This confirmation-only
      todo is satisfied; whether to relaunch it folds into the same open [OPERATOR] scope-decision as the doc's other
      genuinely-absent producers (todos 1-2 above) — not a separate action.
- [x] ✅ [SCRIPT] P3. **DONE — deployment-service@a927715ed6 (reconciled via
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`).** Live-checked both remaining ACTIVE
      genuinely-absent producers: zero running instances, zero relaunch yet (the source doc's `[OPERATOR]`
      relaunch-intent todo is still open, so a genuine production RESOLVED bookend cannot be observed yet). Closed via
      the worker-executable equivalent instead: added
      `test_missing_producer_resolved_bookend_fires_when_producer_relaunches` exercising the full lifecycle end-to-end,
      proving the mechanism itself is correct. Live-verify DP-LIVE-003 correctly RESOLVES (posts a `✅ RESOLVED` bookend
      via `meta_watchers.reconcile_resolved`) for whichever of findings 3-10 get relaunched, confirming the RESOLVED
      path works for this new check type as well as the paging path already confirmed here. Repo: deployment-service.

## Progress Log

- 2026-08-10: Investigated end-to-end. Confirmed the detector (`missing_live_producer_watcher.py`), root-caused the
  burst to the brand-new check's grace-window cold start (contributing factor: a same-day-fixed 300s Cloud Run timeout
  regression on the shared meta-watchers job), verified all 10 prefixes cross-cloud (GCP
  `gcloud compute instances list` + AWS `aws ec2 describe-instances` + `deployments/active/*.json`), fixed the one
  unambiguous detector bug (`agent-orch-planning-vm-`, cross-cloud + stale per-epic-registry mismatch) via
  `deployment-service@be725b0277781b4b3f9d7609254ab82ea9ef4467`, and flagged the remaining 9 (1 likely-same-bug-class
  needing an operator call, 8 confirmed genuinely absent) rather than silently resolving or blind-relaunching.
- 2026-08-10 (follow-up session — 2 coupled pieces of work, both shipped
  `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`): **Part 1 — real AWS liveness for
  `agent-orch-planning-vm-`**: replaced the blanket `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` exclusion with a dedicated
  cross-cloud check (`missing_live_producer_watcher._agent_orch_planning_vm_present`, via new
  `aws_census.describe_ec2_instance_state` — deferred boto3, honest degradation, filters by the orchestrator's EIP
  `13.113.200.22` + instance id `i-0c9b283b31d6b5ca7`). Live-verified with real AWS credentials in this session
  (`aws ec2 describe-instances` → `running`) — the check logic is genuinely correct. Filed a NEW issue,
  `dp_live_003_agent_orch_aws_credentials_gap_2026_08_10.md`, for the confirmed production blocker: the
  `uts-prod-dp-meta-watchers` Cloud Run Job has zero AWS credentials wired in, so in production the check currently
  degrades to `None` every sweep (skip, never page) — same net effect as the prior exclusion until credentials are
  provisioned, but the code is real, tested, and self-activates with zero further code change once that happens. **Part
  2 — formal `not_yet_active`/`superseded` producer lifecycle state**: new
  `deployment_service.data_pipeline_monitors.producer_lifecycle` module (`ProducerLifecycleState` enum: `ACTIVE` /
  `NOT_YET_ACTIVE` / `SUPERSEDED`), consulted by `missing_live_producer_watcher.live_producer_prefixes()` before a
  prefix is evaluated. Explicitly LINKED to `launcher_registry.LAUNCHER_FOR_VM_PREFIX`'s existing `None` = "not
  auto-relaunchable" convention (module docstring explains the correlation + why it's evidence-gated rather than derived
  — `None`-ness alone over-fires on active Cloud-Run-Job-class entries like `manifest-consolidator-`), with a guard test
  (`test_not_yet_active_launcher_registry_correlation_documented_subset`) keeping the two registries from silently
  drifting apart on the subset where they're claimed to overlap. 6 of the burst's 8 genuinely-absent producers (findings
  4/5/6/8/9/10) classified `NOT_YET_ACTIVE` — each has zero `instances.insert`/`.delete` audit-log events in the 90-day
  window (never operated, not "recently stopped"). The remaining 2 (findings 3/7, `mdps-features-live-tradfi-` and
  `prediction-arb-detector-`) have real past-operation history and were deliberately left `ACTIVE`/alerting per
  fail-toward-alerting — a new, narrower `[OPERATOR]` todo scopes just these 2. `mtds-live-prediction-` (finding 2)
  resolved to `SUPERSEDED` (superseded by the already-registered, currently-3-VMs-running `prediction-live-` prefix)
  rather than left ambiguous. Regression tests added for all three required properties: the AWS check reports real state
  correctly (mocked + live-verified out-of-band), a `NOT_YET_ACTIVE` producer never pages when absent, and an `ACTIVE`
  producer (including the 2 ambiguous-but- regression-shaped ones) still pages when genuinely absent. Evidence:
  `quality-gates.sh --no-fix` ALL PASSED (314s, sentinel `b35b5e0fd9c4a6fcb3901622e3c5670b224fdcb5`); shipped via
  quickmerge, landed on `live-defi-rollout` at `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`
  (ancestry-verified against origin).
- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-16** [body-hash:83cc19e793382ee1]: KEEP-NA, valid — Read end-to-end. 4 of 5 todos closed across a same-day follow-up session that shipped a formal ProducerLifecycleState mechanism (classifying 6 of 8 genuinely-absent producers NOT_YET_ACTIVE per the operator's own confirmation that these are pre-live-trading placeholders) plus a real dedicated AWS EC2 liveness check replacing an earlier blanket GCP-only exclusion for the orchestrator VM.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-19 (slot-31, data_pipeline_failure, escalation `agt-7f6044`, `DP_CRON_DID_NOT_FIRE`/DP-LIVE-003 re-page)**:
  DP-LIVE-003 paged again for `mdps-features-live-tradfi-` — the exact producer the still-open `[OPERATOR]` todo below
  already names. Live-verified 2026-08-19: `gcloud compute instances list --filter="name~'^mdps-features-live-tradfi-'"`
  returns zero rows across all zones — genuinely still absent, not a stale/dedup-defeated re-fire artifact (the
  2026-08-17/18 dedup-defeat bugs tracked in `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md` +
  `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` are about repeated pages for the SAME still-true
  condition, not about this condition being false). No new root cause found — this is the same producer, same open
  decision, now 9 days stale. Per this session's role contract (data_pipeline_failure: diagnose or ask, never guess an
  operator-gated relaunch), did not file a duplicate issue doc (findings-triage: "fits another plan → annotate it,
  don't fix") and did not relaunch — escalated the stale `[OPERATOR]` todo below via `/blocked` instead. No code
  changed this session.
- **2026-08-19 (slot-7, data_pipeline_failure, escalation `agt-90f371`, `DP_CRON_DID_NOT_FIRE`/DP-LIVE-003 re-page)**:
  DP-LIVE-003 paged again for `prediction-arb-detector-` — the other still-open `[OPERATOR]` todo in this doc (ran
  continuously until deleted 2026-06-29, ~7 weeks absent at this page). Live-verified 2026-08-19: `gcloud compute
  instances list --filter="name~prediction-arb-detector"` returns zero rows across all zones (project-wide; the same
  census correctly lists the other live producers — `prediction-live-*`, `mtds-live-tradfi-cme-trades-`, etc. — so it
  is not blind). No new root cause — same producer, same open decision, now ~7 weeks stale. The launcher
  (`launch-prediction-arb-detector.sh`) and the features-service `--operation arb-detect` entrypoint are verified
  intact, so a relaunch would be mechanical. Per this session's role contract (data_pipeline_failure: diagnose or ask,
  never guess an operator-gated relaunch/reclassify), did not file a duplicate issue doc (findings-triage: "fits
  another plan → annotate it, don't fix") and did not relaunch — escalated the decision via `/blocked`
  (`BLK-ad065277`: A reclassify `NOT_YET_ACTIVE` [worker rec, consistent with the 2026-08-19 tradfi ruling in
  `agt-7f6044`] vs B relaunch now), the same mechanism the sibling todo used. No answer within the 2-min bounded wait —
  slot freed, question persists for the operator, a later answer re-dispatches a fresh worker. No code changed this
  session.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-20 (slot-32, data_pipeline_failure, escalation `agt-f989d9`, `DP_CRON_DID_NOT_FIRE`/DP-LIVE-003 re-page)**:
  DP-LIVE-003 paged again for `prediction-arb-detector-` — same open `[OPERATOR]` todo above, now ~8 weeks absent
  (deleted 2026-06-29). No new root cause; same known decision point as `agt-90f371` (2026-08-19). Per role contract,
  did not guess a relaunch/reclassify decision and did not file a duplicate issue doc. Escalated via `/blocked`
  (`BLK-3b05bf55`: A reclassify `NOT_YET_ACTIVE` [worker rec] vs B relaunch now). No answer within the 2-min bounded
  wait — slot freed, question persists for the operator, a later answer re-dispatches a fresh worker. No code changed
  this session. **Pattern note for the operator**: this is now the THIRD consecutive re-page (2026-08-19 `agt-90f371`,
  2026-08-19 `BLK-ad065277`, 2026-08-20 `BLK-3b05bf55`) with zero answers — each spawns a fresh worker that burns a
  full diagnosis cycle re-confirming the same already-known fact. Recommend the operator either answer the open
  `[OPERATOR]` todo directly in this doc (bypassing the blocked-question mechanism entirely) or explicitly accept
  option A (reclassify `NOT_YET_ACTIVE`) to stop the alert until a deliberate relaunch decision is made.
- **2026-08-20 (slot-9, data_pipeline_failure, escalation `agt-66493f`, `DP_CRON_DID_NOT_FIRE`/DP-LIVE-003 re-page)**:
  DP-LIVE-003 paged again for `prediction-arb-detector-` — same open `[OPERATOR]` todo. Live-verified: `gcloud compute
  instances list --filter="name~prediction-arb-detector"` zero rows across all zones; census not blind (other live
  producers list fine). Escalated via `/blocked` (`BLK-adfa52fd`); operator answered **A — reclassify
  `NOT_YET_ACTIVE`**, and explicitly asked this worker to actually land the code (noting 3 prior sessions reached the
  same answer without landing it). Added `"prediction-arb-detector-"` to
  `producer_lifecycle.NOT_YET_ACTIVE_PREFIXES`, updated its docstring, and flipped the two regression tests that
  previously asserted the opposite (`test_producer_lifecycle.py::test_ambiguous_burst_producer_stays_active_not_silenced`
  → `test_prediction_arb_detector_reclassified_not_yet_active`;
  `test_missing_live_producer_watcher.py::test_ambiguous_burst_producer_absent_still_pages` →
  `test_prediction_arb_detector_absent_never_pages`). `quality-gates.sh --no-fix` ALL PASSED (271s); shipped via
  quickmerge, landed on `live-defi-rollout`, ancestry-verified — `deployment-service@27e9f53cd4`. This resolves the
  last open half of the `[OPERATOR]` todo above (the `mdps-features-live-tradfi-` half was already resolved
  2026-08-19). **`archive_exempt: true` added**: all todos are now done, but this doc is cited as the DP-LIVE-003
  false-positive/ambiguous-producer reference from 8 other active docs (`tradfi_satellite_ao_dispatch_batch12`,
  `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17`, `dp_live_003_agent_orch_aws_credentials_gap_2026_08_10`, and
  5 more) — archiving now would require a referrer-path sweep out of scope for this one-shot escalation; standing
  reference value + the referrer fan-out justify exemption over immediate archival.

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
    /plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md,
    /plans/active/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-08-10
author: sub-agent (Claude Code session, dispatched to root-cause + fix the DP_CRON_DID_NOT_FIRE burst)
parent_epic: infrastructure_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-10
locked_since:
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

- [ ] [OPERATOR] P1. Decide the fate of finding 2 (`mtds-live-prediction-`): was the 2026-06-28 consolidated-migration
      abandoned by design (→ drop the `mtds-live-prediction-` registry entry from DP-LIVE-003's scope, mirroring the
      agent-orch-planning-vm- fix) or should it be revived (→ this is instead evidence of the SAME genuine-gap class as
      findings 3-10, and the consolidated VM needs relaunching)? Repo: deployment-service.
- [ ] [OPERATOR] P1. For each of the 8 confirmed-genuinely-absent producers (findings 3-10), confirm operational intent:
      currently expected to be always-on (real regression, needs relaunch) vs. not-yet-rolled-out-to-prod (registry got
      ahead of the actual deployment, DP-LIVE-003 correctly catching a real gap but not an urgent one). Do not relaunch
      blind — each producer's current config/entrypoint needs a fresh look before restart. Repo: deployment-service.
- [ ] [SCRIPT] P2. Also confirm `prediction-live-kalshi-book-snapshot-5-*` (the 4th documented
      `launch-prediction-live.sh` shard, not currently running) — noted in finding 2's evidence, outside this doc's
      original 10-prefix scope but the same investigation surfaced it. Repo: deployment-service.
- [ ] [SCRIPT] P3. Live-verify DP-LIVE-003 correctly RESOLVES (posts a `✅ RESOLVED` bookend via
      `meta_watchers.reconcile_resolved`) for whichever of findings 3-10 get relaunched, confirming the RESOLVED path
      works for this new check type as well as the paging path already confirmed here. Repo: deployment-service.

## Progress Log

- 2026-08-10: Investigated end-to-end. Confirmed the detector (`missing_live_producer_watcher.py`), root-caused the
  burst to the brand-new check's grace-window cold start (contributing factor: a same-day-fixed 300s Cloud Run timeout
  regression on the shared meta-watchers job), verified all 10 prefixes cross-cloud (GCP
  `gcloud compute instances list` + AWS `aws ec2 describe-instances` + `deployments/active/*.json`), fixed the one
  unambiguous detector bug (`agent-orch-planning-vm-`, cross-cloud + stale per-epic-registry mismatch) via
  `deployment-service@be725b0277781b4b3f9d7609254ab82ea9ef4467`, and flagged the remaining 9 (1 likely-same-bug-class
  needing an operator call, 8 confirmed genuinely absent) rather than silently resolving or blind-relaunching.
